import {
  AfterContentInit,
  ChangeDetectionStrategy,
  Component,
  ContentChildren,
  OnDestroy,
  Optional,
  QueryList,
  Self,
} from '@angular/core';
import { ControlValueAccessor, NgControl } from '@angular/forms';

import { startWith, takeUntil } from 'rxjs/operators';
import { merge, Subject } from 'rxjs';

import { ModelZooFilterComponent } from './model-zoo-filter/model-zoo-filter.component';

interface IFormValue {
  [key: string]: unknown;
}

@Component({
  selector: 'wb-model-zoo-filter-group',
  templateUrl: './model-zoo-filter-group.component.html',
  styleUrls: ['./model-zoo-filter-group.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModelZooFilterGroupComponent implements OnDestroy, AfterContentInit, ControlValueAccessor {
  @ContentChildren(ModelZooFilterComponent) filterList: QueryList<ModelZooFilterComponent<unknown>>;

  private readonly _unsubscribe$ = new Subject<void>();

  private _onChange = (_: IFormValue) => {};
  private _onTouched = () => {};

  constructor(@Self() @Optional() private readonly _controlDirective: NgControl) {
    if (this._controlDirective) {
      this._controlDirective.valueAccessor = this;
    }
  }

  ngAfterContentInit(): void {
    this.filterList.changes
      .pipe(startWith(null as unknown), takeUntil(this._unsubscribe$))
      .subscribe(() => this._resetOptions());
  }

  ngOnDestroy(): void {
    this._unsubscribe$.next();
    this._unsubscribe$.complete();
  }

  private _resetOptions(): void {
    const changedOrDestroyed$ = merge(this.filterList.changes, this._unsubscribe$);

    merge(...this.filterList.map((filter) => filter.optionsChange))
      .pipe(takeUntil(changedOrDestroyed$))
      .subscribe(() => this._emitChanges());
  }

  writeValue(): void {}

  registerOnChange(fn: (value: IFormValue) => {}): void {
    this._onChange = fn;
  }

  registerOnTouched(fn: () => {}): void {
    this._onTouched = fn;
  }

  private _emitChanges(): void {
    const value: IFormValue = {};
    for (const filter of this.filterList) {
      value[filter.group] = Array.from(filter.selectedOptions);
    }
    this._onTouched();
    this._onChange(value);
  }
}
